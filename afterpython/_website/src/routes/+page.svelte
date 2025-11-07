<script lang="ts">
  import type { PageProps } from './$types';
  import MarkdownRenderer from '$components/MarkdownRenderer.svelte';
  import StarIcon from '$components/StarIcon.svelte';

  const { data: metadataJson }: PageProps = $props();

  // Extract repository URL safely
  const repositoryUrl: string | undefined = metadataJson.project_url?.find((url: string) =>
    url.startsWith('repository,')
  )?.split(', ')[1];

  // Page-specific title
  const pageTitle = metadataJson.name
    ? `${metadataJson.name} - Home`
    : 'Home';
</script>

<svelte:head>
  <title>{pageTitle}</title>
  {#if metadataJson.summary}
		<meta name="description" content={metadataJson.summary} />
	{/if}
</svelte:head>

{#if metadataJson.metadataError}
  <!-- Error state: metadata.json is missing -->
  <section class="flex mt-[12vh] flex-col gap-6 items-center justify-center min-h-[60vh] text-center px-4">
    <div class="w-full max-w-2xl px-6 py-8 bg-bg200 rounded-2xl shadow-lg border-2 border-pm500">
      <h1 class="text-4xl font-bold text-pm500 mb-4">500</h1>
      <p class="text-xl text-tx100 mb-2 text-left">
        {metadataJson.metadataError}
      </p>
    </div>
  </section>
{:else}
  <!-- Normal state: metadata loaded successfully -->
  <section class="flex mt-[12vh] flex-col gap-6 items-center justify-center min-h-[60vh] text-center px-4">
    <h1 class="text-6xl md:text-7xl font-bold tracking-tight text-tx50">
      {metadataJson.name}
    </h1>
    <p class="text-xl md:text-2xl text-tx300 max-w-2xl">
      {metadataJson.summary}
    </p>

    <div class="flex gap-4 flex-wrap justify-center">
      {#if repositoryUrl}
        <a
          href={repositoryUrl}
          target="_blank"
          rel="noopener noreferrer"
          class="group px-6 py-3 bg-yellow-400 dark:bg-yellow-400 text-gray-900 dark:text-gray-900 rounded-lg font-semibold hover:bg-yellow-500 dark:hover:bg-yellow-500 transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl transform hover:scale-105"
        >
          <StarIcon size={20} filled={true} class="star-blink" />
          Star on GitHub
        </a>
      {/if}
      <button class="px-6 py-3 bg-pm500 text-white rounded-lg font-medium hover:bg-pm600 transition-colors">
        Go to Playground
      </button>
    </div>

    {#if metadataJson.description}
      <div class="w-full max-w-4xl px-6 py-8 bg-bg100 rounded-2xl shadow-lg border border-bg300 text-left">
        <MarkdownRenderer content={metadataJson.description} />
      </div>
    {/if}
  </section>
{/if}

<style>
  @keyframes star-blink {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.2); }
  }

  :global(.star-blink) {
    animation: star-blink 1.5s ease-in-out infinite;
  }
</style>