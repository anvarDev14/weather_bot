from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = "7928128631:AAH5tdOKkdjF_3J7Z7quULd6oLUG-hrbmyE"
ADMINS = [6369838846,7872028789]  # Добавьте свой ID
WEATHER_API_KEY = '8aab62712df12fec699d40dc4c82467d'