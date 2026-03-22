import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def audit_gemini():
    api_key = os.getenv('GEMINI_API_KEY', '').split(',')[0].strip()
    if not api_key:
        print("❌ لا يوجد مفتاح API.")
        return

    print(f"📡 فحص شامل للمفتاح: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        
        print("\n📋 قائمة الموديلات المتاحة لك فعلياً من جوجل:")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ متاح: {m.name}")
                available_models.append(m.name)
        
        if not available_models:
            print("🛑 خطأ كارثي: مفتاحك لا يملك صلاحية لأي موديل! تأكد من تفعيله في Google AI Studio.")
            return

        # تجربة أول موديل متاح في القائمة لضمان النجاح 100%
        target = available_models[0]
        print(f"\n🚀 تجربة الاتصال الرسمية بموديل: {target}")
        model = genai.GenerativeModel(target)
        response = model.generate_content("قُل تم الاتصال بنجاح")
        print(f"💎 النتيجة المذهلة: {response.text}")
        
    except Exception as e:
        print(f"❌ فشل الفحص الشامل. السبب: {str(e)}")

if __name__ == "__main__":
    audit_gemini()
