from django import forms
from .models import AcademicSession
class SessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = ['label', 'course_code']
class UploadForm(forms.Form):
    session = forms.ModelChoiceField(queryset=AcademicSession.objects.order_by('-id'))
    kind = forms.ChoiceField(choices=[('workbook', 'Evaluation workbook (.xlsx)'), ('roster', 'Official student roster (.csv)'), ('assignments', 'Evaluator assignments (.csv)')])
    file = forms.FileField()
    def clean_file(self):
        f = self.cleaned_data['file']
        if f.size > 12 * 1024 * 1024: raise forms.ValidationError('Maximum upload is 12 MB.')
        return f

class ProfileForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False, label='First name')
    last_name = forms.CharField(max_length=150, required=False, label='Last name')
    email = forms.EmailField(required=False, label='Contact email')
    photo = forms.FileField(required=False, label='Profile photo (JPEG, PNG or WebP; maximum 2 MB)')
    remove_photo = forms.BooleanField(required=False, label='Remove my current photo')
    current_password = forms.CharField(required=False, widget=forms.PasswordInput, label='Current password (required to change email)')

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data.get('email', '').strip() != self.user.email and not self.user.check_password(data.get('current_password', '')):
            self.add_error('current_password', 'Enter your current password to change the contact email.')
        if data.get('photo') and data.get('remove_photo'):
            self.add_error('photo', 'Choose a new photo or remove the old photo, not both.')
        return data

    def clean_photo(self):
        upload = self.cleaned_data.get('photo')
        if not upload:
            return None
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Maximum photo size is 2 MB.')
        import io, warnings
        from PIL import Image, ImageOps, UnidentifiedImageError
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                image = Image.open(upload)
                if image.format not in ('JPEG', 'PNG', 'WEBP') or getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Unsupported photo format.')
                if image.width * image.height > 16000000:
                    raise ValueError('Photo resolution too large.')
                image.load()
                image = ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'), (256, 256))
                # A fresh raster discards EXIF/GPS, comments and any appended payload.
                clean = Image.frombytes('RGB', image.size, image.tobytes())
                output = io.BytesIO()
                clean.save(output, format='JPEG', quality=85)
                return output.getvalue()
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise forms.ValidationError('Use a valid, still JPEG, PNG or WebP photo up to 16 megapixels.') from error
