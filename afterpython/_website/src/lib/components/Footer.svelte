<script lang="ts">
	import GitHubIcon from '$components/GitHubIcon.svelte';

	type FooterProps = {
		projectName?: string;
		repositoryUrl?: string;
		docsUrl?: string;
		projectSummary?: string;
	}

	let { projectName, repositoryUrl, docsUrl, projectSummary }: FooterProps = $props();

	const currentYear = new Date().getFullYear();
</script>

<footer class="bg-bg100 border-t border-bg300 mt-auto">
	<div class="container mx-auto px-4 py-8">
		<!-- Main Footer Content -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-16 mb-8 max-w-4xl mx-auto">
			<!-- Project Info -->
			<div>
				{#if projectName}
					<div class="flex items-center gap-2 mb-3">
						{#if repositoryUrl}
							<a
								href={repositoryUrl}
								target="_blank"
								rel="noopener noreferrer"
								class="text-tx300 hover:text-tx50 transition-colors"
								aria-label="GitHub Repository"
							>
								<GitHubIcon size={18} />
							</a>
						{/if}
						<h3 class="text-lg font-semibold text-tx50">{projectName}</h3>
					</div>
					<p class="text-sm text-tx300">
						{projectSummary}
					</p>
				{/if}
			</div>

			<!-- Resources -->
			<div>
				<h3 class="text-lg font-semibold text-tx50 mb-3">Resources</h3>
				<ul class="space-y-2 text-sm text-tx300">
					{#if docsUrl}
						<li><a href={docsUrl} target="_blank" rel="noopener noreferrer" class="hover:text-tx50 transition-colors">Documentation</a></li>
					{/if}
					<li><a href="/tutorials" class="hover:text-tx50 transition-colors">Tutorials</a></li>
					<li><a href="/examples" class="hover:text-tx50 transition-colors">Examples</a></li>
					<li><a href="/blog" class="hover:text-tx50 transition-colors">Blog</a></li>
				</ul>
			</div>
		</div>

		<!-- Bottom Bar -->
		<div class="border-t border-bg300 pt-6 max-w-4xl mx-auto">
			<div class="flex flex-col md:flex-row items-center justify-between gap-4">
				<!-- Copyright -->
				<div class="text-sm text-tx300">
					{#if projectName}
						© {currentYear} {projectName}. All rights reserved.
					{:else}
						© {currentYear} All rights reserved.
					{/if}
				</div>

				<!-- Powered by AfterPython -->
				<div class="flex items-center gap-2 text-sm text-tx300">
					<img src="/afterpython.svg" alt="AfterPython" class="h-5 w-auto" />
					<span>Powered by <a href="https://afterpython.org" target="_blank" rel="noopener noreferrer" class="text-tx50 hover:text-pm500 transition-colors font-medium">AfterPython</a></span>
				</div>
			</div>
		</div>
	</div>
</footer>
