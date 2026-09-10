# encoding: utf-8
#
# Points the site at a different address.
#
# Page-to-page links and images are all relative, so they work anywhere without
# help. But a few things need to know the site's real, absolute address:
# canonical tags, Open Graph URLs, sitemap.xml, robots.txt, and the <base> tag
# on 404.html. This updates all of them at once.
#
#   ruby tools/set_site_url.rb https://www.cincinnatikcpc.com
#   ruby tools/set_site_url.rb https://yechani33.github.io/KCPC
#
# Moving to the custom domain? Run it with the real URL, then re-create the
# CNAME file (it must contain exactly: www.cincinnatikcpc.com) and push.

require "uri"

ROOT = File.expand_path("..", __dir__)

new_url = ARGV[0].to_s.strip.sub(%r{/+\z}, "")
if new_url.empty? || !new_url.start_with?("http")
  abort "usage: ruby tools/set_site_url.rb https://example.com[/subpath]"
end

index = File.join(ROOT, "index.html")
abort "cannot find index.html" unless File.exist?(index)

old_url = File.read(index, encoding: "UTF-8")[%r{<link rel="canonical" href="([^"]+)"}, 1].to_s.sub(%r{/+\z}, "")
abort "cannot find a canonical URL in index.html" if old_url.empty?

if old_url == new_url
  puts "already set to #{new_url} — nothing to do"
  exit 0
end

puts "#{old_url}  ->  #{new_url}"

targets = Dir[File.join(ROOT, "*.html")] +
          Dir[File.join(ROOT, "*/index.html")] +
          [File.join(ROOT, "sitemap.xml"), File.join(ROOT, "robots.txt")]

changed = 0
targets.each do |path|
  next unless File.exist?(path)
  s = File.read(path, encoding: "UTF-8")
  hits = s.scan(old_url).size
  next if hits.zero?
  s.gsub!(old_url, new_url)
  File.write(path, s)
  changed += 1
  puts format("  %-24s %d", path.sub(ROOT + "/", ""), hits)
end

# 404.html is served for any missing path, however deep, so relative URLs on it
# would resolve against the wrong directory. A <base> keeps it anchored.
base_path = URI(new_url).path rescue ""
base_path = "/" if base_path.nil? || base_path.empty?
base_path += "/" unless base_path.end_with?("/")

not_found = File.join(ROOT, "404.html")
if File.exist?(not_found)
  s = File.read(not_found, encoding: "UTF-8")
  if s.sub!(/<base href="[^"]*">/, %(<base href="#{base_path}">))
    File.write(not_found, s)
    puts format("  %-24s base -> %s", "404.html", base_path)
  end
end

puts "updated #{changed} file(s)"
