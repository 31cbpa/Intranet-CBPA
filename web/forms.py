from django import forms
from .models import Firefighter, EmergencyContact
from django.forms import inlineformset_factory

class FirefighterForm(forms.ModelForm):
    class Meta:
        model = Firefighter
        fields = [
            'company', 'registration_number', 'entry_date', 'quality', 'position', 'email',
            'first_name', 'paternal_surname', 'maternal_surname', 'rut', 'birth_date',
            'gender', 'address', 'commune', 'contact_number', 'personal_email'
        ]
        widgets = {
            'entry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese nombre'}),
            'paternal_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese apellido paterno'}),
            'maternal_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese apellido materno'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 123456'}),
            'quality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Voluntario'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bombero, Teniente'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678-9'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese dirección'}),
            'commune': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese comuna'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +56 9 1234 5678'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo.personal@ejemplo.com'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(FirefighterForm, self).__init__(*args, **kwargs)
        # Marcar campos obligatorios visualmente
        for field_name in ['company', 'registration_number', 'entry_date', 'quality', 'position', 
                          'email', 'first_name', 'paternal_surname', 'maternal_surname']:
            self.fields[field_name].label = f"{self.fields[field_name].label} *"

    def clean_rut(self):
        """Validación básica de RUT chileno"""
        rut = self.cleaned_data.get('rut')
        if rut:
            rut = rut.replace(".", "").replace("-", "")
            if len(rut) < 2:
                raise forms.ValidationError("RUT inválido: demasiado corto")
            body, dv = rut[:-1], rut[-1].upper()
            
            try:
                body = int(body)
            except ValueError:
                raise forms.ValidationError("RUT inválido: debe contener solo números y guión")
                
            # Formatear RUT
            formatted_rut = f"{body:,}".replace(",", ".") + "-" + dv
            return formatted_rut
        return rut

class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ['first_name', 'paternal_surname', 'maternal_surname', 'relationship', 'contact_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'paternal_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido paterno'}),
            'maternal_surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido materno'}),
            'relationship': forms.Select(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: +56 9 1234 5678'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(EmergencyContactForm, self).__init__(*args, **kwargs)
        # Marcar campos obligatorios visualmente
        for field_name in ['first_name', 'paternal_surname', 'maternal_surname', 'relationship', 'contact_number']:
            self.fields[field_name].label = f"{self.fields[field_name].label} *"

# Formset para manejar múltiples contactos de emergencia
EmergencyContactFormSet = inlineformset_factory(
    Firefighter, 
    EmergencyContact, 
    form=EmergencyContactForm,
    extra=1,
    can_delete=True,
    validate_max=True,
    min_num=1,  # Al menos un contacto de emergencia
    validate_min=True
)

# Formulario de búsqueda para filtrar bomberos
class FirefighterSearchForm(forms.Form):
    search = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por nombre, rut o registro'})
    )
    company = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Todas las compañías",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo'})
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Company
        super(FirefighterSearchForm, self).__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()