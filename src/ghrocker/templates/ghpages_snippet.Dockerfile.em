ENV DEBIAN_FRONTEND noninteractive
RUN echo "gem: --no-document" > ~/.gemrc
RUN gem install bundler
RUN gem install jekyll
# Add -f to override conflicting executable between sass and sass-embedded
RUN gem install -f github-pages
RUN gem install jekyll-include-cache

EXPOSE 4000
