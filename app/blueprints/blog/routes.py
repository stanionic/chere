from flask import render_template, request
from app.blueprints.blog import blog_bp
from app.models import Article


@blog_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("category")
    query = Article.query.filter_by(is_published=True)
    if category:
        query = query.filter_by(category=category)
    pagination = query.order_by(Article.published_at.desc()).paginate(page=page, per_page=9, error_out=False)
    return render_template("blog/index.html", pagination=pagination, articles=pagination.items)


@blog_bp.route("/<slug>")
def detail(slug):
    article = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("blog/post.html", article=article)
