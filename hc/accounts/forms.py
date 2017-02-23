from django import forms
from hc.accounts.models import ACCEPT_DAILY_REPORTS, ACCEPT_WEEKLY_REPORTS, ACCEPT_MONTHLY_REPORTS, UNSUBSCRIBE_REPORTS


class LowercaseEmailField(forms.EmailField):

    def clean(self, value):
        value = super(LowercaseEmailField, self).clean(value)
        return value.lower()


class EmailPasswordForm(forms.Form):
    email = LowercaseEmailField()
    password = forms.CharField(required=False)


class ReportSettingsForm(forms.Form):
    CHOICES = ((ACCEPT_DAILY_REPORTS, 'Each day send me a summary of my checks',),
               (ACCEPT_WEEKLY_REPORTS, 'Each week send me a summary of my checks',),
               (ACCEPT_MONTHLY_REPORTS, 'Each month send me a summary of my checks',),
               (UNSUBSCRIBE_REPORTS, 'Do not send me Periodic reports',))
    reports_allowed = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES)


class SetPasswordForm(forms.Form):
    password = forms.CharField()


class InviteTeamMemberForm(forms.Form):
    email = LowercaseEmailField()


class RemoveTeamMemberForm(forms.Form):
    email = LowercaseEmailField()


class TeamNameForm(forms.Form):
    team_name = forms.CharField(max_length=200, required=True)
