import pexpect
import time
import hashlib
import base64


def change_system_password(system_user, new_password):

    p = pexpect.spawn('sudo', ['passwd', system_user], timeout=5)

    for i in range(2):
        p.expect('new.*password.*:')
        time.sleep(0.5)
        p.sendline(new_password)

    p.expect('.*success')


def _hashed_token(token, salt, length):
    # The `token` is the "DEVICE_TOKEN" that this device uses to authenticate
    # with the AutoAuto servers. It is stored in a permission-locked file that
    # only `root` can access. The `token` is unique to this device; it is set
    # _once_ when the device is first configured, and it should remain secret
    # for all of eternity.
    #
    # This function takes that `token`, and uses it to generate other secrets.
    # Namely, it is used to generate two other secrets:
    #
    #   1. It will be used to generate the default password for the privileged
    #      system user on this device (e.g. used by the owner of the device to
    #      `ssh` into the device). It is important that every device has a
    #      strong & unique default system password [1], thus using the `token`
    #      to generate it is a good solution.
    #
    #   2. It will be used to generate the password used to access this device's
    #      Jupyter server. It is important that the Jupyter server is locked-down
    #      (for obvious reasons), so once again, we'll use the `token` to create
    #      a strong & unique password to protect the Jupyter server running on this
    #      device.
    #
    # Note that the passwords generated here are one-way hashes of the `token`,
    # thus these passwords will not reveal any information about the original
    # token, which is highly important.
    #
    # It is also important that the two uses above result in _different_ passwords.
    # To achieve this we will salt each differently (using the `salt` parameter
    # passed here). They should be _different_ because each grants a different
    # level of access to the device (the first is a _privileged_ system user, while
    # the second is an _unprivileged_ Jupyter server).
    #
    # The password generated by the first usage above will be written-down and
    # sent with the physical device to its owner. It is the responsibility of the
    # owner to (1) keep it secret, and (2) change it (using `passwd`) for the highest
    # amount of security. (Note: This is similar to what WiFi routers do with
    # their devices.)
    #
    # The password generated by the second usage above will not be written-down.
    # Instead it will be used to generate a link to the Jupyter server from the
    # owner's AutoAutoLabs account. Again, it is the owner's responsibility to not
    # share that link.
    #
    # [1] The reason it's important to have strong & unique default passwords
    #     is because we really don't want AutoAuto devices used in an IoT botnet...
    #     we assume you agree :) For example, see [this story](http://goo.gl/sbq4it).

    m = hashlib.sha256()
    m.update(salt.encode('utf-8'))
    m.update(token.encode('utf-8'))
    hash_bytes = m.digest()
    hash_base64 = base64.b64encode(hash_bytes)
    password = hash_base64[:length].decode('utf-8')
    password = password.replace('/', '_').replace('+', '_')  # '/' and '+' are confusing for users to see in a password; this replacement is easier on the eyes and only decreases the level of security by a miniscule amount (the password length is plenty long, and we're just giving up 1 character from an alphabet of 64.)
    return password


def token_to_system_password(token):
    return _hashed_token(token, 'AutoAuto privileged system password salt value!', 12)


def token_to_jupyter_password(token):
    return _hashed_token(token, 'AutoAuto Jupyter server password salt value!', 24)

