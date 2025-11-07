<script lang="ts">
	import '../app.css';
	import type { LayoutProps } from './$types';
	import ThemeToggle from '$components/ThemeToggle.svelte';
	import Logo from '$components/Logo.svelte';
	import Footer from '$components/Footer.svelte';

	let { data: metadataJson, children }: LayoutProps = $props();

	// Extract documentation URL safely
	const docsUrl = metadataJson.project_url?.find((url: string) =>
		url.startsWith('documentation,')
	)?.split(', ')[1];

	// Extract repository URL safely
	const repositoryUrl = metadataJson.project_url?.find((url: string) =>
		url.startsWith('repository,')
	)?.split(', ')[1];

	// Dynamic title from metadata
	const siteTitle = metadataJson.name || 'AfterPython Project Website';
</script>

<svelte:head>
	<title>{siteTitle}</title>
</svelte:head>

<div class="bg-bg50 min-h-screen flex flex-col">
	<nav class="container mx-auto py-3 text-tx50 text-base font-medium">
		<div class="flex items-center">
			<Logo size="md" />
			<ul class="flex gap-18 justify-center flex-1">
				{#if docsUrl}
					<li>
						<a href={docsUrl} target="_blank" rel="noopener noreferrer">
							Documentation
						</a>
					</li>
				{/if}
				<li>
					<a href={'/tutorials'}>Tutorials</a>
				</li>
				<li>
					<a href={'/examples'}>Examples</a>
				</li>
				<li>
					<a href={'/blog'}>Blog</a>
				</li>
				<!-- <li>
					<a href={'/exercises'}>Exercises</a>
				</li>
				<li>
					<a href={'/changelog'}>Changelog</a>
				</li>
				<li>
					<a href={'/community'}>Community</a>
				</li> -->
			</ul>
			<ThemeToggle />
		</div>
	</nav>

	{@render children()}

	<Footer projectName={metadataJson.name} projectSummary={metadataJson.summary} {repositoryUrl} {docsUrl}/>
</div>