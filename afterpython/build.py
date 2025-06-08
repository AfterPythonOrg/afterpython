# Your build script should do this:
def build_blog_posts():
    blog_posts = []
    
    # Process user content from afterpython/blog/
    for content_file in Path("afterpython/blog/").glob("*"):
        if content_file.suffix in ['.md', '.ipynb', '.py']:
            # Convert to HTML
            html_content = process_content_file(content_file)
            slug = content_file.stem
            metadata = extract_metadata(content_file)
            
            # Save HTML in _afterpython subdirectory of build output
            html_path = Path(f"afterpython/_build/_afterpython/blog/{slug}.html")
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(html_content)
            
            # Collect metadata
            blog_posts.append({
                "title": metadata.get("title", slug.replace("-", " ").title()),
                "slug": slug,
                "date": metadata.get("date", "2024-01-01"),
                "excerpt": metadata.get("excerpt", ""),
                "author": metadata.get("author", ""),
                "tags": metadata.get("tags", [])
            })
    
    # Generate blog_posts.json directly in the build output root
    # This makes it available at /blog_posts.json when served
    Path("afterpython/_build/blog_posts.json").write_text(
        json.dumps(blog_posts, indent=2)
    )