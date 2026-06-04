from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Menu


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['nama_makanan', 'kantin', 'harga', 'gambar']
        widgets = {
            'nama_makanan': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'kantin': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'harga': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
            'gambar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RegisterForm(forms.ModelForm):
    """
    Form registrasi dengan email opsional dan konfirmasi sandi.
    Password di-hash Django secara otomatis via user.set_password().
    """
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )
    password1 = forms.CharField(
        label='Sandi',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Konfirmasi Sandi',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        min_length=8,
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Nama pengguna sudah digunakan. Pilih yang lain.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Email ini sudah terdaftar.')
        return email

    def clean_password1(self):
        pw = self.cleaned_data.get('password1')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return pw

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('password1')
        pw2 = cleaned.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            self.add_error('password2', 'Konfirmasi sandi tidak cocok.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class VerifikasiEmailForm(forms.Form):
    """
    Tahap 1 lupa sandi — verifikasi email terdaftar.
    """
    email = forms.EmailField(
        label='Alamat Email',
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                'Email tidak terdaftar. Pastikan email yang kamu masukkan sama '
                'dengan yang digunakan saat registrasi.'
            )
        return email


class ResetPasswordForm(forms.Form):
    """
    Tahap 2 lupa sandi — buat sandi baru.
    Password di-hash Django via user.set_password().
    """
    password1 = forms.CharField(
        label='Sandi Baru',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Konfirmasi Sandi Baru',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        min_length=8,
    )

    def clean_password1(self):
        pw = self.cleaned_data.get('password1')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return pw

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('password1')
        pw2 = cleaned.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            self.add_error('password2', 'Konfirmasi sandi tidak cocok.')
        return cleaned


# Kept for backward compatibility (used by old lupa_password view if still referenced)
class LupaPasswordForm(forms.Form):
    username  = forms.CharField(label='Nama Pengguna', max_length=150)
    password1 = forms.CharField(label='Sandi Baru', widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label='Konfirmasi Sandi Baru', widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned  = super().clean()
        username = cleaned.get('username')
        pw1      = cleaned.get('password1')
        pw2      = cleaned.get('password2')
        if username and not User.objects.filter(username=username).exists():
            self.add_error('username', 'Nama pengguna tidak ditemukan.')
        if pw1 and pw2 and pw1 != pw2:
            self.add_error('password2', 'Konfirmasi sandi tidak cocok.')
        return cleaned