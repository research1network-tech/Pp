'use client';

export const dynamic = 'force-dynamic';

import React, { useState } from 'react';

export default function TelegramLogin() {
  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  // طلب الكود
  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone) {
      setMessage('الرجاء إدخال رقم الهاتف.');
      setIsError(true);
      return;
    }
    setLoading(true);
    setMessage('');

    try {
      const res = await fetch('/api/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'SEND_CODE', phone }),
      });
      const data = await res.json();

      if (res.ok && data.success) {
        setMessage('تم إرسال كود التحقق إلى حسابك في تيليجرام.');
        setIsError(false);
        setStep('OTP');
      } else {
        setMessage(data.error || 'فشل إرسال الكود. تأكد من إعدادات الـ API.');
        setIsError(true);
      }
    } catch (err) {
      setMessage('حدث خطأ في الاتصال بالخادم.');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  // التحقق من الكود
  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp) {
      setMessage('الرجاء إدخال كود التحقق.');
      setIsError(true);
      return;
    }
    setLoading(true);
    setMessage('');

    try {
      const res = await fetch('/api/telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'VERIFY_CODE', code: otp }),
      });
      const data = await res.json();

      if (res.ok && data.success) {
        setMessage('تم تسجيل الدخول وربط الحساب بنجاح تام! 🟢');
        setIsError(false);
      } else {
        setMessage(data.error || 'كود التحقق غير صحيح.');
        setIsError(true);
      }
    } catch (err) {
      setMessage('حدث خطأ أثناء التحقق.');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
        
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-blue-500 mb-2">تسجيل دخول تيليجرام</h1>
          <p className="text-gray-400 text-sm">أدخل رقم هاتفك للبدء</p>
        </div>

        {message && (
          <div className={`p-3 rounded-xl mb-6 text-sm text-center border ${isError ? 'bg-red-900/40 border-red-600 text-red-200' : 'bg-green-900/40 border-green-600 text-green-200'}`}>
            {message}
          </div>
        )}

        {step === 'PHONE' ? (
          <form onSubmit={handleRequestCode} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">رقم الهاتف (مع رمز الدولة)</label>
              <input
                type="text"
                required
                placeholder="+9665xxxxxxxx"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-4 py-3 bg-gray-950 border border-gray-800 rounded-xl text-white text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
                dir="ltr"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl transition shadow-lg disabled:opacity-50"
            >
              {loading ? 'جاري الإرسال...' : 'إرسال كود التحقق'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyCode} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">أدخل الكود المرسل لتيليجرام</label>
              <input
                type="text"
                required
                maxLength={6}
                placeholder="12345"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                className="w-full px-4 py-3.5 bg-gray-950 border border-gray-800 rounded-xl text-white text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3.5 rounded-xl transition shadow-lg disabled:opacity-50"
            >
              {loading ? 'جاري التحقق...' : 'تأكيد الدخول'}
            </button>

            <button
              type="button"
              onClick={() => setStep('PHONE')}
              className="text-sm text-gray-400 hover:text-white transition block mx-auto mt-2"
            >
              إعادة إدخال الرقم
            </button>
          </form>
        )}

      </div>
    </main>
  );
}
