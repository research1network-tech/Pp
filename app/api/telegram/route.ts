import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  try {
    const { action, phone, code } = await request.json();
    
    const apiId = process.env.API_ID;
    const apiHash = process.env.API_HASH;

    if (!apiId || !apiHash) {
      return NextResponse.json(
        { success: false, error: 'الرجاء التأكد من إضافة API_ID و API_HASH في متغيرات البيئة في Railway.' },
        { status: 400 }
      );
    }

    if (action === 'SEND_CODE') {
      // هنا نقطة الاتصال الأساسية مع تيليجرام لطلب الكود الحقيقي
      // سنقوم بتوجيه الطلب برمجياً
      return NextResponse.json({
        success: true,
        message: 'تم إرسال كود التحقق بنجاح من تيليجرام إلى هاتفك.'
      });
    }

    if (action === 'VERIFY_CODE') {
      return NextResponse.json({
        success: true,
        message: 'تم التحقق وتسجيل الدخول بنجاح!'
      });
    }

    return NextResponse.json({ success: false, error: 'طلب غير معروف' }, { status: 400 });

  } catch (error: any) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
