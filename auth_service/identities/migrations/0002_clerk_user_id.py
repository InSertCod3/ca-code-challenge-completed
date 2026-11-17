from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("identities", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="user",
            name="clerk_user_id",
            field=models.CharField(max_length=160, unique=True, null=True, blank=True),
        )
    ]
