rm -f db.sqlite3
rm -rf crowdsourcedtagging/migrations
rm -rf crowdsourcedtagging/images
python3 manage.py makemigrations crowdsourcedtagging
python3 manage.py migrate
chmod 755 db.sqlite3
sudo chown www-data:www-data db.sqlite3
