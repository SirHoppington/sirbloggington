from app import db


tag_blog = db.Table('tag_blog',
                    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
                    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id'), primary_key=True)
                    )


topic_blog = db.Table('topic_blog',
                    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id'), primary_key=True),
                    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'), primary_key=True)
                    )


series_blog = db.Table('series_blog',
                    db.Column('series_id', db.Integer, db.ForeignKey('series.id'), primary_key=True),
                    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id'), primary_key=True)
                    )
