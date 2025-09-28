<script lang="ts">
	import { resolve } from '$app/paths';
  
  const { data } = $props();
</script>

<div>
  <h1>Blogs:</h1>
  <br />
  {#each data.blogPosts as post}
    <div>
      <h2>{post.title}</h2>
      <p>{post.excerpt}</p>
      <a href={resolve(`/blog/${post.slug}`)} class="read-more">
        Read More →
      </a>
    </div>
  {/each}
</div>