from packaging.version import Version as BaseVersion


class Version(BaseVersion):
    def next_breaking(self, level: str = "auto") -> "Version":
        """Get the next version that would break compatibility.
        
        Args:
            level: "major", "minor", or "auto" (detect from current version)
                   - If major == 0: breaks on minor (0.x API is unstable)
                   - If major >= 1: breaks on major (semver stable)
        
        Examples:
            Version("0.9.7").next_breaking() -> Version("0.10.0")
            Version("1.2.3").next_breaking() -> Version("2.0.0")
            Version("1.2.3").next_breaking("minor") -> Version("1.3.0")
        """
        if level == "auto":
            # Follow semver convention: 0.x.x breaks on minor, 1.x.x+ breaks on major
            level = "minor" if self.major == 0 else "major"
        
        if level == "major":
            return Version(f"{self.major + 1}.0.0")
        elif level == "minor":
            return Version(f"{self.major}.{self.minor + 1}.0")
        else:
            raise ValueError(f"Invalid level: {level}. Use 'major', 'minor', or 'auto'")
    
    def bump_major(self) -> "Version":
        """Bump major version. Example: 1.2.3 -> 2.0.0"""
        return Version(f"{self.major + 1}.0.0")
    
    def bump_minor(self) -> "Version":
        """Bump minor version. Example: 0.9.7 -> 0.10.0"""
        return Version(f"{self.major}.{self.minor + 1}.0")
    
    def bump_patch(self) -> "Version":
        """Bump patch version. Example: 0.9.7 -> 0.9.8"""
        return Version(f"{self.major}.{self.minor}.{self.micro + 1}")
