from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        exclude = ['created_at', 'updated_at']
        widgets = {
            'town': forms.Select(),
            'state': forms.TextInput(attrs={'value': 'PR', 'readonly': 'readonly', 'class': 'bg-gray-100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'h-5 w-5 text-orange-600 focus:ring-orange-500 border-gray-300 rounded'})
            else:
                field.widget.attrs.update({'class': 'w-full border border-gray-300 rounded p-2 focus:ring-orange-500 focus:border-orange-500 bg-white'})