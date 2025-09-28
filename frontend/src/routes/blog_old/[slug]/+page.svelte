<script lang="ts">
    import { page } from '$app/state';
    import { onMount } from 'svelte';
    
    let blogPosts = $state([]);
    let htmlContent = $state('');
    let postMeta = $state(null);
    let loading = $state(true);
    let error = $state(null);
    
    onMount(async () => {
      const slug = page.params.slug;
      
      try {
        // Find the post metadata from imported JSON
        const response = await fetch('./blog_posts.json');
        blogPosts = await response.json();
        postMeta = blogPosts.find(p => p.slug === slug);
        
        if (!postMeta) {
          throw new Error('Post not found');
        }
        
        // Try to load the HTML content
        const htmlResponse = await fetch(postMeta.htmlPath);
        if (!htmlResponse.ok) {
          // For development, create some mock HTML content
          htmlContent = `
            <p>This is mock content for <strong>${postMeta.title}</strong>.</p>
            <p>${postMeta.excerpt}</p>
            <p>In production, this would be the actual HTML content generated from your .md, .ipynb, or .py files.</p>
          `;
        } else {
          htmlContent = await htmlResponse.text();
        }
        
      } catch (err) {
        error = err.message;
      } finally {
        loading = false;
      }
    });
  </script>
  
  {#if loading}
    <div class="loading">Loading...</div>
  {:else if error}
    <div class="error">Error: {error}</div>
  {:else if postMeta}
    <article class="blog-post">
      <header class="post-header">
        <h1>{postMeta.title}</h1>
        <div class="post-meta">
          <span class="date">{new Date(postMeta.date).toLocaleDateString()}</span>
          {#if postMeta.author}
            <span class="author">by {postMeta.author}</span>
          {/if}
        </div>
        {#if postMeta.tags}
          <div class="tags">
            {#each postMeta.tags as tag}
              <span class="tag">{tag}</span>
            {/each}
          </div>
        {/if}
      </header>
      
      <div class="post-content">
        {@html htmlContent}
      </div>
      
      <nav class="post-nav">
        <a href="/blog">← Back to Blog</a>
      </nav>
    </article>
  {:else}
    <div class="error">Post not found</div>
  {/if}
  
  <style>
    .blog-post {
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
    }
  
    .post-header {
      margin-bottom: 2rem;
      border-bottom: 1px solid #eee;
      padding-bottom: 1rem;
    }
  
    .post-header h1 {
      font-size: 2.5rem;
      margin-bottom: 1rem;
      color: #1a1a1a;
    }
  
    .post-meta {
      color: #666;
      margin-bottom: 1rem;
    }
  
    .author {
      margin-left: 1rem;
    }
  
    .tags {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  
    .tag {
      background: #f0f0f0;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.875rem;
    }
  
    .post-content {
      line-height: 1.7;
      margin-bottom: 2rem;
    }
  
    .post-nav a {
      color: #0066cc;
      text-decoration: none;
    }
  
    .post-nav a:hover {
      text-decoration: underline;
    }
  
    .loading, .error {
      text-align: center;
      padding: 2rem;
    }
  
    .error {
      color: #dc3545;
    }
  </style> 