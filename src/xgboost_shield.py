import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
import os
import glob
from src.utils.logger import app_logger

class XGBoostShield:
    def __init__(self, model_path=None):
        # ── [RAILWAY PERSISTENCE FIX] ──
        # Get DB path (which is usually on a persistent volume in Railway like /data/brain.db)
        self.db_path = os.environ.get("DB_PATH", "brain.db")
        
        # Save the model in the exact same folder as the database so it survives Railway redeploys!
        db_dir = os.path.dirname(self.db_path)
        if not db_dir:
            db_dir = "."
            
        self.model_path = model_path or os.path.join(db_dir, "xgboost_shield.json")
        
        self.model = None
        self.is_trained = False
        self.trained_count = 0
        self.min_trades_required = 50
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = xgb.XGBClassifier()
                self.model.load_model(self.model_path)
                self.is_trained = True
                
                # Fetch count from DB for UI
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    self.trained_count = conn.execute("SELECT COUNT(*) FROM trade_memory WHERE strategy_used != 'SOLANA_DEX'").fetchone()[0]
                    conn.close()
                except:
                    self.trained_count = "150+" # Fallback
                    
                app_logger.info(f"🧠 [XGBOOST] Loaded existing model (trained on ~{self.trained_count} trades).")
            except Exception as e:
                app_logger.error(f"🧠 [XGBOOST] Error loading model: {e}")
                self.is_trained = False
                self.trained_count = 0

    def _get_training_data(self, db_paths, limit=1000):
        """Extract recent trades from databases."""
        dfs = []
        for db_path in db_paths:
            if not os.path.exists(db_path):
                continue
            try:
                conn = sqlite3.connect(db_path)
                query = "SELECT profit_loss, ai_confidence, market_health, strategy_used, sentiment FROM trade_memory WHERE strategy_used != 'SOLANA_DEX'"
                df = pd.read_sql_query(query, conn)
                dfs.append(df)
            except Exception as e:
                app_logger.warning(f"Error reading {db_path}: {e}")
        
        if not dfs:
            return pd.DataFrame()
            
        final_df = pd.concat(dfs, ignore_index=True)
        # Drop rows with NaN in critical columns
        final_df = final_df.dropna(subset=['profit_loss', 'ai_confidence', 'market_health'])
        # Get the most recent `limit` trades (assuming order implies recency)
        return final_df.tail(limit)

    def _preprocess_data(self, df):
        """Convert raw DB rows to feature matrix X and labels y."""
        if df.empty:
            return None, None
            
        # Target: 1 if trade was profitable (Win), 0 if loss (Fakeout/Loss)
        y = (df['profit_loss'] > 0).astype(int)
        
        # Features
        X = pd.DataFrame()
        X['ai_confidence'] = pd.to_numeric(df['ai_confidence'], errors='coerce').fillna(50.0)
        X['market_health'] = pd.to_numeric(df['market_health'], errors='coerce').fillna(50.0)
        
        # One-hot encode strategy (limit to top common strategies to avoid feature explosion)
        if 'strategy_used' in df.columns:
            strategy_dummies = pd.get_dummies(df['strategy_used'], prefix='strat')
            # Keep only a few to avoid sparsity issues for small datasets
            X = pd.concat([X, strategy_dummies], axis=1)
            
        # Sentiment mapping
        if 'sentiment' in df.columns:
            sent_map = {'BULLISH': 1, 'BEARISH': -1, 'NEUTRAL': 0}
            X['sentiment_score'] = df['sentiment'].str.upper().map(sent_map).fillna(0)
            
        return X, y

    def train(self, force=False):
        """Train or retrain the XGBoost model."""
        # Check the actual DB_PATH and backups in the same folder
        db_dir = os.path.dirname(self.db_path) or "."
        db_paths = [self.db_path] + glob.glob(os.path.join(db_dir, "PROSOFT_BRAIN_BACKUP_*.db"))
        
        df = self._get_training_data(db_paths, limit=1000)
        
        if len(df) < self.min_trades_required:
            app_logger.info(f"🧠 [XGBOOST] Not enough data to train. Found {len(df)} trades, need {self.min_trades_required}.")
            return False
            
        X, y = self._preprocess_data(df)
        if X is None or len(X) == 0:
            return False
            
        try:
            # We save the feature names used during training so inference matches exactly
            self.feature_columns = list(X.columns)
            
            # Initialize XGBClassifier
            model = xgb.XGBClassifier(
                n_estimators=100, 
                max_depth=4, 
                learning_rate=0.1, 
                eval_metric='logloss',
                random_state=42
            )
            
            model.fit(X, y)
            self.model = model
            self.is_trained = True
            
            # Save the model
            self.model.save_model(self.model_path)
            
            # Save feature columns as a simple text file
            with open(self.model_path + ".features", "w") as f:
                f.write(",".join(self.feature_columns))
                
            self.trained_count = len(X)
            app_logger.info(f"🧠 [XGBOOST] Successfully trained on {self.trained_count} trades. Win Rate in data: {(y.sum()/len(y)*100):.1f}%")
            return True
        except Exception as e:
            app_logger.error(f"🧠 [XGBOOST] Training error: {e}")
            return False

    def predict_fakeout(self, ai_confidence, market_health, strategy_used="Unknown", sentiment="NEUTRAL"):
        """
        Returns the probability (0.0 to 1.0) that this trade is a FAKEOUT (will lose).
        """
        if not self.is_trained or self.model is None:
            return 0.0 # Cannot predict, assume safe
            
        try:
            # Load feature columns if available
            feature_cols = ['ai_confidence', 'market_health', 'sentiment_score']
            if os.path.exists(self.model_path + ".features"):
                with open(self.model_path + ".features", "r") as f:
                    feature_cols = f.read().split(",")
                    
            # Build input dataframe matching exactly the training columns
            input_dict = {col: 0 for col in feature_cols}
            
            input_dict['ai_confidence'] = float(ai_confidence)
            input_dict['market_health'] = float(market_health)
            
            sent_map = {'BULLISH': 1, 'BEARISH': -1, 'NEUTRAL': 0}
            if 'sentiment_score' in input_dict:
                input_dict['sentiment_score'] = sent_map.get(str(sentiment).upper(), 0)
                
            strat_key = f"strat_{strategy_used}"
            if strat_key in input_dict:
                input_dict[strat_key] = 1
                
            X_infer = pd.DataFrame([input_dict])
            
            # predict_proba returns [[prob_loss, prob_win]]
            probs = self.model.predict_proba(X_infer)[0]
            prob_fakeout = float(probs[0]) # Probability of class 0 (Loss)
            
            return prob_fakeout
            
        except Exception as e:
            app_logger.error(f"🧠 [XGBOOST] Inference error: {e}")
            return 0.0
