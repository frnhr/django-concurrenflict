from django import forms
from django.core import serializers


class ConcurrenflictFormMixin(forms.ModelForm):

    # TODO: make it hide the colon before our empty label - move the whole thing to .as_p() et al.
    concurrenflict_initial = forms.CharField(
        widget=forms.HiddenInput,
        label="",
        required=False)

    _concurrenflict_json_data = ''

    concurrenflict_field_name = 'concurrenflict_initial'

    def _get_concurrenflict_field(self):
        return self.fields[self.concurrenflict_field_name]

    def __init__(self, *args, **kwargs):
        super(ConcurrenflictFormMixin, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            opts = self._meta
            object_data = forms.model_to_dict(instance, opts.fields, opts.exclude)
            self._concurrenflict_json_data = serializers.serialize('json',  [instance], fields=object_data.keys())
            self._get_concurrenflict_field().initial = self._concurrenflict_json_data


    def clean(self):
        # The 'model_json' field is hidden, and as such the user can't change it
        # (at least without hacking on the POST data).
        # So the value we get back for the 'model_json' field is effectively the value
        # it was set to by a previous instance of this form's __init(), when the form
        # was created to send the data to the user on the GET.
        #
        # Our instance was instantiated on the POST, and so we too will have set model_json's
        # initial value based on the state of the model at the time of the POST.
        #
        # So the apparent new value is the value from the original GET and the apparent
        # old value, the 'initial' value is the value from the time of the POST.
        #
        # Normally those will be the same, since we've not yet saved any changes the user
        # has made (we're about to validate those changes now...). However, if someone
        # else changed the model in the meantime, then those two values will no longer match,
        # and that's what we're trying to catch.
        json_at_get = self.cleaned_data[self.concurrenflict_field_name]
        #json_at_get = self._get_concurrenflict_field().widget.value_from_datadict(self.data, self.files, self.add_prefix('model_json'))
        json_at_post = self._concurrenflict_json_data

        # if json_at_post is None then this is an add() rather than a change(), so
        # there's no old record that could have changed while this one was being worked on
        if json_at_post and (json_at_post != json_at_get):
            raise forms.ValidationError("Foo record has changed since you started editing it.")

        return self.cleaned_data