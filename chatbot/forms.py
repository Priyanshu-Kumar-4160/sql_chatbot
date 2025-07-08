from django import forms

class QueryForm(forms.Form):
    user_input = forms.CharField(
        label = "Ask a question about the data",
        widget = forms.Textarea(attrs={"rows":3, "placeholder":"e.g. List customers from Delhi"})
    )
