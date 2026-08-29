from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('tolmach', '0022_remove_usermeta_email'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Make column nullable FIRST so the data fixes below can actually hold NULL
                # (Django's builtin auth migration creates this column as NOT NULL).
                "ALTER TABLE auth_user MODIFY email varchar(254) NULL;",
                "UPDATE auth_user SET email = NULL WHERE email = '';",
                # Resolve duplicates: keep the oldest account per email, NULL the rest
                # (MySQL UNIQUE treats NULLs as distinct, so multiple NULL emails are fine).
                """UPDATE auth_user u
                   LEFT JOIN (
                       SELECT email, MIN(id) AS keep_id
                       FROM auth_user
                       WHERE email IS NOT NULL AND email <> ''
                       GROUP BY email
                       HAVING COUNT(*) > 1
                   ) d ON u.email = d.email
                   SET u.email = NULL
                   WHERE u.email IS NOT NULL AND u.email <> ''
                     AND u.id <> d.keep_id;""",
                "ALTER TABLE auth_user ADD UNIQUE INDEX auth_user_email_uniq (email);",
            ],
            reverse_sql=[
                "ALTER TABLE auth_user DROP INDEX auth_user_email_uniq;",
                "UPDATE auth_user SET email = '' WHERE email IS NULL;",
                "ALTER TABLE auth_user MODIFY email varchar(254) NOT NULL;",
            ],
        ),
    ]