import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from src.utils.logger import app_logger


class ModelManager:
    def __init__(self, model_path='data/random_forest_model.pkl'):
        self.model_path   = model_path
        self.scaler_path  = model_path.replace('.pkl', '_scaler.pkl')
        self.model        = None
        self.scaler       = None
        self.last_accuracy = 0.0

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if os.path.exists(self.scaler_path):
                    self.scaler = joblib.load(self.scaler_path)
                app_logger.info(f"AI Model loaded from {self.model_path}.")
            except Exception as e:
                app_logger.error(f"Error loading AI Model: {e}")

    # ── Features ─────────────────────────────────────────────────────────────

    FEATURE_COLS = ['RSI', 'MACD_HIST', 'DIST_EMA_50', 'volume', 'ATR',
                    'BB_WIDTH', 'MOM_10']

    def prepare_features(self, df):
        available = [c for c in self.FEATURE_COLS if c in df.columns]
        features  = df[available].copy()

        if 'volume' in features.columns and 'VOLUME_SMA' in df.columns:
            sma = df['VOLUME_SMA'].replace(0, np.nan)
            features['volume'] = (features['volume'] / sma).fillna(1.0)

        return features.fillna(0)

    # ── Training ──────────────────────────────────────────────────────────────

    def train_model(self, df, lookahead_period=12):
        """
        Train on: will close be higher in `lookahead_period` candles?
        Uses GradientBoosting for better edge over RandomForest.
        """
        df = df.copy()
        df['future_close'] = df['close'].shift(-lookahead_period)
        df['target']       = (df['future_close'] > df['close'] * 1.005).astype(int)

        X = self.prepare_features(df)
        y = df['target']

        valid = df.dropna().index
        X, y  = X.loc[valid], y.loc[valid]

        if len(X) < 200:
            app_logger.warning("Insufficient data for training (need ≥ 200 samples).")
            return False

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )

        self.scaler  = StandardScaler()
        X_train_sc   = self.scaler.fit_transform(X_train)
        X_test_sc    = self.scaler.transform(X_test)

        self.model   = GradientBoostingClassifier(
            n_estimators=200, max_depth=4,
            learning_rate=0.05, random_state=42
        )
        self.model.fit(X_train_sc, y_train)

        preds              = self.model.predict(X_test_sc)
        self.last_accuracy = accuracy_score(y_test, preds)
        app_logger.info(f"AI Model trained. Test Accuracy: {self.last_accuracy:.4f}")

        joblib.dump(self.model,  self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        return True

    # ── Prediction ────────────────────────────────────────────────────────────

    def calculate_confidence(self, current_data_row):
        """
        Returns a REAL confidence score derived from either:
          1. Trained model probability (if model exists)
          2. Composite technical score (if no model yet)
        Never returns a static/random value.
        """
        if self.model is not None and self.scaler is not None:
            try:
                available = [c for c in self.FEATURE_COLS if c in current_data_row]
                row_data  = {}
                for col in available:
                    row_data[col] = current_data_row[col]
                    if col == 'volume' and current_data_row.get('VOLUME_SMA', 0) > 0:
                        row_data[col] = current_data_row['volume'] / current_data_row['VOLUME_SMA']

                feat_df   = pd.DataFrame([row_data]).fillna(0)
                feat_sc   = self.scaler.transform(feat_df)
                proba     = self.model.predict_proba(feat_sc)[0]
                return float(proba[1])  # probability of class=1 (price goes up)
            except Exception as e:
                app_logger.warning(f"Model prediction error, falling back: {e}")

        # ── Fallback: real technical composite ──────────────────────────────
        return self._technical_confidence(current_data_row)

    def _technical_confidence(self, row):
        """
        Calculates confidence purely from technical indicators.
        Range: 0.15 – 0.95. No randomness.
        """
        score = 0.35  # neutral baseline

        rsi      = float(row.get('RSI',        50))
        macd     = float(row.get('MACD_HIST',   0))
        dist     = float(row.get('DIST_EMA_50', 0))
        bb_w     = float(row.get('BB_WIDTH',  0.02))
        mom      = float(row.get('MOM_10',      0))

        # RSI zone
        if 45 <= rsi <= 65:   score += 0.18   # momentum sweet spot
        elif 30 <= rsi < 45:  score += 0.22   # oversold recovery
        elif rsi < 30:        score += 0.25   # deep oversold bounce
        elif rsi > 75:        score -= 0.15   # overbought — risky

        # MACD histogram direction
        if macd > 0:    score += 0.12
        elif macd < 0:  score -= 0.08

        # Price vs EMA_50 position
        if dist > 0.01:   score += 0.10   # above EMA: bullish
        elif dist < -0.03: score -= 0.10  # too far below: risky reversal

        # Momentum
        if 1 < mom < 5:   score += 0.08
        elif mom > 8:     score -= 0.05   # parabolic move = risky entry

        # Volatility squeeze = breakout incoming
        if bb_w < 0.015:  score += 0.05

        return round(min(0.95, max(0.15, score)), 3)
