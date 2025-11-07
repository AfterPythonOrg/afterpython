import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async () => {
  try {
    // Dynamic import to handle missing file gracefully
    const metadata = await import('$static/metadata.json');
    return {
      ...metadata.default,
      metadataError: null,
    };
  } catch {
    // metadata.json is missing or invalid - return minimal data to keep layout working
    return {
      name: '',
      summary: '',
      description: '',
      project_url: [],
      metadataError: 'Project metadata not found. Please ensure metadata.json exists in the static folder. Did you forget to run `ap build`?',
    };
  }
};