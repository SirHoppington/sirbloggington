#!/usr/bin/env python3
from app import create_app, db
from app.Blog.blog_model import Blog
from slugify import slugify

app = create_app()
app.app_context().push()

blogs = Blog.query.all()
seen = {}

for blog in blogs:
    base = slugify(blog.title)
    slug = base

    # ensure uniqueness
    if base in seen:
        seen[base] += 1
        slug = f"{base}-{seen[base]}"
    else:
        seen[base] = 1

    blog.slug = slug

db.session.commit()
print("Slugs generated successfully!")
