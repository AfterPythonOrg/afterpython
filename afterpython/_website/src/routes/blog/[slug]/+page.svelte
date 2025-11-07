<script lang="ts">
  
  const { data } = $props();
</script>

<div>
  <a href={`/blog`} class="back-to-blog">← Back to Blog</a>
  <h1>{data.post?.title}</h1>
  <p>{data.post?.excerpt}</p>
  <p>{data.post?.content}</p>
</div>