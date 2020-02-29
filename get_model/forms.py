from django import forms

class GetDataForm(forms.Form) :
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())

class RevokeTaskForm(forms.Form) :
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())

class TrainForm(forms.Form) :

    # Embedding layer (128) min=max_features
    output_dim = forms.IntegerField(label="Output dim (Embedding layer)", widget=forms.NumberInput(), initial=128)

    # LSTM units (128): Positive integer, dimensionality of the output space.
    lstm_units = forms.IntegerField(label="LSTM units", widget=forms.NumberInput(), initial=128)

    # Dropout rate (0.5)
    drop_rate = forms.FloatField(label="Dropout rate (float)", widget=forms.NumberInput(), initial=0.5)

    # Activation func ('sigmoid')
    ACT_FUNC_CHOICES = (
    ('sigmoid', 'sigmoid'),
    ('relu', 'relu')) 
    act_func = forms.ChoiceField(label="Activation function", choices=ACT_FUNC_CHOICES, 
                                widget=forms.Select(), required=True, initial='sigmoid')

    # Epoch
    epochs = forms.IntegerField(label="Epoch", widget=forms.NumberInput(),  initial=1)

    # batch_size
    batch_size = forms.IntegerField(label="Batch size", widget=forms.NumberInput(),  initial=128)