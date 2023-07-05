from app.Series.series_model import Series
from app import db



def add_series(data, new_blog):
        series_exists = db.session.query(Series).filter(
            Series.name == data).first()
        if series_exists:
            new_blog.series.append(series_exists)
        else:
            new_series = Series(name=data)
            new_blog.series.append(new_series)
            db.session.add(new_series)