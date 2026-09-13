source "https://rubygems.org"

# Jekyll en su versión 4.x. GitHub Pages se construye aquí con
# GitHub Actions, no con el modo "deploy from a branch", así que
# no estamos atados a la gema github-pages ni a Jekyll 3.
gem "jekyll", "~> 4.4"

group :jekyll_plugins do
  gem "jekyll-feed",     "~> 0.17"   # RSS/Atom automático
  gem "jekyll-sitemap",  "~> 1.4"    # sitemap.xml para buscadores
  gem "jekyll-seo-tag",  "~> 2.8"    # metadatos Open Graph y Twitter
end

# Windows y JRuby no traen la base de datos de husos horarios; hace falta
# esta gema para que `timezone: Europe/Madrid` funcione.
platforms :windows, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# Acelera el vigilante de archivos en Windows. En Linux no se instala.
gem "wdm", "~> 0.2", platforms: :windows

# Desde Ruby 3.4 estas dejaron de venir de serie.
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"

# Servidor local moderno (Ruby 3 ya no incluye webrick).
gem "webrick", "~> 1.8"
