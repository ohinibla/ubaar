class OTP:

    @staticmethod
    def send_sms(phonenumber):
        print(f"send message to {phonenumber}")

    @staticmethod
    def generate_random_otp():
        from random import randint

        return "".join([str(randint(0, 9)) for _ in range(6)])
