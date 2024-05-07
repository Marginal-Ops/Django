module purge;
module load anaconda3;
export PYTHONPATH=$(pwd)
# python3 manage.py makemigrations
# python3 manage.py migrate
python3 manage.py runserver 0.0.0.0:8001
