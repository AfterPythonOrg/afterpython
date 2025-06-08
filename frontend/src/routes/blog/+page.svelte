<script lang="ts">
  import blogPosts from '$lib/blog_posts.json';
</script>

<div class="blog-container">
  <h1>Blog</h1>
  
  <div class="blog-grid">
    {#each blogPosts as post}
      <article class="blog-card">
        <div class="blog-card-content">
          <h2 class="blog-title">{post.title}</h2>
          <p class="blog-date">{new Date(post.date).toLocaleDateString()}</p>
          {#if post.excerpt}
            <p class="blog-excerpt">{post.excerpt}</p>
          {/if}
          {#if post.tags && post.tags.length > 0}
            <div class="tags">
              {#each post.tags as tag}
                <span class="tag">{tag}</span>
              {/each}
            </div>
          {/if}
          <a href="/blog/{post.slug}" class="read-more">
            Read More →
          </a>
        </div>
      </article>
    {/each}
  </div>
</div>

<style>
  .blog-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .blog-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
  }

  .blog-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .blog-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  }

  .blog-card-content {
    padding: 1.5rem;
  }

  .blog-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
    color: #1a1a1a;
  }

  .blog-date {
    font-size: 0.875rem;
    color: #666;
    margin: 0 0 1rem 0;
  }

  .blog-excerpt {
    color: #4a4a4a;
    line-height: 1.6;
    margin: 0 0 1rem 0;
  }

  .tags {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
  }

  .tag {
    background: #f0f0f0;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    color: #666;
  }

  .read-more {
    color: #0066cc;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .read-more:hover {
    text-decoration: underline;
  }

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1a1a1a;
    text-align: center;
    margin-bottom: 1rem;
  }

  .loading, .no-posts {
    text-align: center;
    padding: 2rem;
    color: #666;
  }
</style>
