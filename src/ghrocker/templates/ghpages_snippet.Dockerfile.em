ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -q -y curl net-tools python3 python3-yaml build-essential nodejs ruby-full autoconf automake libtool pkg-config zlib1g-dev
RUN echo "gem: --no-document" > ~/.gemrc
RUN gem install bundler
RUN gem install jekyll
# Add -f to override conflicting executable between sass and sass-embedded
RUN gem install -f github-pages
RUN gem install jekyll-include-cache

EXPOSE 4000
