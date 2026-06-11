import os
import replicate
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HairTryOnRequest

# ربط الـ Token بالبيئة لتتعرف عليه مكتبة Replicate تلقائياً
os.environ["REPLICATE_API_TOKEN"] = settings.REPLICATE_API_TOKEN

@csrf_exempt
def generate_haircut_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'الطلب يجب أن يكون من نوع POST'}, status=405)

    # 1. استقبال الملفات والبيانات القادمة من الموبايل
    user_img_file = request.FILES.get('user_image')
    haircut_name = request.POST.get('haircut_name', '')
    reference_img_file = request.FILES.get('reference_image')

    if not user_img_file:
        return JsonResponse({'error': 'من فضلك قم برفع صورة الوجه أولاً'}, status=400)

    # 2. حفظ الطلب في قاعدة البيانات بحالة "pending"
    try_on_request = HairTryOnRequest.objects.create(
        user_image=user_img_file,
        haircut_name=haircut_name,
        reference_image=reference_img_file,
        status='pending'
    )

    try:
        haircut_query = haircut_name.strip().lower() if haircut_name else ""

        # وصف دقيق جداً وصارم يجبر الموديل على تثبيت النظارة والملامح المصرية والقميص
        if "أصلع" in haircut_name or "bald" in haircut_query:
            prompt_text = (
                "Photo of the exact same man in the input image wearing his black glasses, "
                "same face, same body weight, same nose, same expressions, and same maroon shirt. "
                "The ONLY modification is his head: make the top of his head completely bald and clean shaved. "
                "Do not change his identity, do not remove his glasses, do not change his background. "
                "Just shave his hair completely bald."
            )
        elif haircut_name:
            prompt_text = (
                f"Photo of the exact same man in the input image wearing his black glasses and maroon shirt. "
                f"Modify ONLY his hair to a realistic {haircut_name} haircut. "
                "Keep his face identity, face shape, nose, eyes, and skin tone 100% unchanged. "
                "Only change the hairstyle layout."
            )
        else:
            prompt_text = (
                "Photo of the exact same man in the input image wearing his black glasses. "
                "Modify ONLY his hair to a short clean men haircut, keeping his exact face and identity."
            )
        
        # تحضير رابط الصورة المحلية
        user_image_url = request.build_absolute_uri(try_on_request.user_image.url)

        # 3. استدعاء الموديل المجاني المتاح في حسابك مع بارامترز صارمة جداً
        output = replicate.run(
            "black-forest-labs/flux-kontext-pro",
            input={
                "image": user_image_url,
                "prompt": prompt_text,
                "negative_prompt": (
                    "white European guy, different person, slim face, change face shape, "
                    "remove glasses, look like a different man, beautiful model, wig, blurry"
                ),
                "steps": 20,              # عدد خطوات أقل يمنع الموديل من تخيل تفاصيل بعيدة عن الأصل
                "guidance_scale": 4.5,     # تقليل التوجيه النصي لكي يعتمد الموديل أكثر على تفاصيل الصورة الأصلية
                "prompt_strength": 0.15,   # النسبة السحرية! (0.15) تعني الحفاظ على 85% من الصورة الأصلية (الوجه والقميص والنظارة) وتعديل 15% فقط (الشعر)
                "control_strength": 0.95
            }
        )

        # 4. معالجة النتيجة وحفظها
        if output:
            generated_url = output.url if hasattr(output, 'url') else str(output)

            try_on_request.generated_image_url = generated_url
            try_on_request.status = 'completed'
            try_on_request.save()

            return JsonResponse({
                'status': 'success',
                'message': 'تم معالجة الصورة بنجاح وتثبيت الملامح!',
                'result_image': generated_url
            })
        else:
            raise Exception("لم يتم استلام رابط صورة من الـ API")

    except Exception as e:
        try_on_request.status = 'failed'
        try_on_request.save()
        return JsonResponse({
            'status': 'failed',
            'message': 'حدث خطأ أثناء معالجة الصورة بالذكاء الاصطناعي',
            'error': str(e)
        }, status=500)