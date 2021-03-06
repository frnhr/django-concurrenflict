django-concurrenflict
=====================

Prevent concurrency conflicts in Django ModelForms by failing validation and showing the user what has changed.

Mainly designed for Django admin, but should work just as well in any `ModelForm`. Works with **Django 1.6**+.

## The Problem Scenario

 0. User opens a `SomeModel` instance for editing in a view that contains a `ModelForm`.
 0. While she is editing the object, something\_or\_someone also edits and saves it.
 0. User submits the form. 
 
Concurrency problem just happened: the edits from step 2 are lost! And nobody had any warning or a chance to do something about it.
 
## Solution

**django-concurrenflict** kicks in at step 2, before the `SomeModel` is saved.

 * The `ModelForm` will fail validation (i.e. the `SomeModel` instance won't be saved)
 * User will be presented with a non-field-error: "This record has changed since you started editing it."
 * User will also be presented with a "This field has changed! New Value:" message on every field that has changed.
 * The message will be followed by a read-only widget (using disabled="disabled") that shows the modified value. (Technically, the widget is part of the validation error message.)
 
 * If the `SomeModel` instance has been modified, but the submitted changes are not in conflict with the modifications, then nothing will happen, i.e. the save will proceed as usual.

## Screenshots

Frontend (using django-bootstrap-toolkit for CSS, but works regardless of any custom CSS)

![Frontend form](docs_img/bootstrap.png)

Admin

![Admin form](docs_img/admin.png)

Looks much better with Grappelli

![Admin form](docs_img/grappelli.png)



## Implementation & Usage

**django-concurrenflict** provides `ConcurrenflictFormMixin` mixin. The mixin adds a json hidden field to the form. On `clean()` the content of json field is compared against the being edited (fetched fresh from the database). If conflicting modifications are found, field validation fails.

There are two similar options for usage.

### A) add `ConcurrenflictFormMixin` to forms

Add the mixin to existing `ModelForm` classes:

    class MyModel(ConcurrenflictFormMixin, ModelForm):
        ....
        
### B) import `ModelForm` from concurrenflict

substitute 

	from django.forms import ModelForm
	
with:

    from concurrenflict import ModelForm

    # no need to edit anything else, provided that the Forms are defined thus:
    
    class MyModel(ModelForm):
        ....

If `ModelForm` are extending `forms.ModelForm` then minor edits are needed to remove "forms."


## Credits

The inspiration came from a post by **David-761** in [this forum thread][1] and [this pastebin][2].


## Todo & Ideas

 * Write da tests!
 * Option to use sessions storage instead of json field.
 * Test against Django 1.7a
 * Feature for django-admin: AJAX notice when two users are editing the same object
 * Feature for django-admin: option to save last request.user and show it in the error (if it was a user)


[1]: http://python.6.x6.nabble.com/Admin-interface-not-preventing-simultaneous-editing-of-the-same-record-td502368.htmt    "Admin interface not preventing simultaneous editing of the same record"
[2]: http://pastebin.com/f3b2c03cb    "FooAdminForm"

