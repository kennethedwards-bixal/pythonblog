from django.shortcuts import get_object_or_404, render, get_list_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity

# class PostListView(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'

def post_list(request, tag_slug= None):
    object_list = Post.published.all()
    tag = None
    
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3) # 3 posts per page
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        #if page not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        #if page is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)


    return render(request, 'blog/post/list.html', {'page': page, 'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status = 'published', publish__year=year, publish__month = month, publish__day=day)

    # list active comments for this post
    comments = post.comments.filter(active=True)

    new_comment = None

    if request.method == 'POST':
        # a comment was posted
        comment_form = CommentForm(data=request.POST)
        
        if comment_form.is_valid():
            # create commnet object but dont save to DB yet
            new_comment = comment_form.save(commit=False)
            #assign the current post to the comment
            # doing this, specifies new commet belongs this post
            new_comment.post = post
            # save the comment to the database
            new_comment.save()
    else:
        # create a comment form instance with A GET to the post detail
        comment_form = CommentForm()

    # list simular posts
    # You retrieve a Python list of IDs for the tags of the current post. 
    # The values_ list() QuerySet returns tuples with the values for the given fields. 
    # You pass flat=True to it to get single values such as [1, 2, 3, ...] instead
    # of one-tuples such as [(1,), (2,), (3,) ...].
    post_tags_ids = post.tags.values_list('id', flat=True)
    # You get all posts that contain any of these tags, excluding the current post itself.
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    # You use the Count aggregation function to generate a 
    # calculated field—same_ tags—that contains the number of tags shared with all the tags queried.
    # You order the result by the number of shared tags (descending order) and by publish 
    # to display recent posts first for the posts with the same number of shared tags. 
    # You slice the result to retrieve only the first four posts.
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]


    return render(
        request, 
        'blog/post/detail.html', 
        {'post': post,
          'comments': comments,
          'new_comment': new_comment,
          'comment_form': comment_form,
          'simular_posts': similar_posts      
        })

def post_share(request, post_id):
    #retrieve by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # forms fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " f"{post.title}"
            message = f"Read {post.title} at {post_url}" f"{cd['name']}\s comments: {cd['comments']}"
            send_mail(subject, message, 'ken@myblog.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    
    return render(request, 'blog/post/share.html', {'post':post, 'form': form,'sent': sent})


# You send the form using the GET method instead of POST, so 
# that the resulting URL includes the query parameter and is 
# easy to share. When the form is submitted, you instantiate 
# it with the submitted GET data, and verify that the form data is valid. 
# If the form is valid, you search for published posts with a 
# custom SearchVector instance built with the title and body fields.

def post_search(request):
    form = SearchForm()
    query = None
    results = []
    # if form is submitted
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            # You can boost specific vectors so that more weight is attributed to them when ordering results by relevancy. 
            # For example, you can use this to give more relevance to posts that are matched by title rather than by content.
            search_vector = SearchVector('title', weight= 'A') + SearchVector('body', weight = 'B')
            search_query = SearchQuery(query)
            # ----
            results = Post.published.annotate(
                # In the preceding code, you create a SearchQuery object, 
                # filter results by it, and use SearchRank to order the results by relevancy.
                search = search_vector,
                rank= SearchRank(search_vector, search_query)

            ).filter(rank__gte=0.3).order_by('-rank')
            # ---=
            # results = Post.published.annotate(similarity=TrigramSimilarity('title', query), ).filter(similarity__gt=0.1).order_by('-similarity')

    return render(request, 'blog/post/search.html', {
        'form': form,
        'query': query,
        'results': results
    })

# maybe try installing directly next time
# https://stackoverflow.com/questions/64712167/error-while-configuring-postgressql-for-django