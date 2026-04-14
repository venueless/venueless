FROM python:3.14-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN curl -sL https://deb.nodesource.com/setup_20.x | bash && \
    apt-get install -y --no-install-recommends \
            build-essential \
            git \
            locales \
            libpq-dev \
            libssl-dev \
            libxml2-dev \
            libxslt1-dev \
            nginx \
            python3-dev \
            sudo \
            supervisor \
            poppler-utils \
            nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    dpkg-reconfigure locales && \
	locale-gen C.UTF-8 && \
	/usr/sbin/update-locale LANG=C.UTF-8 && \
    mkdir /etc/venueless && \
    mkdir -p /venueless/webapp && \
    mkdir /data && \
    useradd -ms /bin/bash -d /venueless -u 15371 venueless && \
    echo 'venueless ALL=(ALL) NOPASSWD:SETENV: /usr/bin/supervisord' >> /etc/sudoers && \
    mkdir /static

ENV LC_ALL=C.UTF-8 \
    DJANGO_SETTINGS_MODULE=venueless.settings \
	IPYTHONDIR=/data/.ipython \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install locked dependencies. Doing this before copying the source means this
# layer is only rebuilt when pyproject.toml or uv.lock change.
COPY server/pyproject.toml server/uv.lock /venueless/server/
RUN cd /venueless/server && \
    uv sync --locked --no-install-project && \
    uv pip install ipython && \
    rm -rf /root/.cache/uv

COPY prod/entrypoint.bash /usr/local/bin/venueless
COPY prod/supervisord.conf /etc/supervisord.conf
COPY prod/nginx.conf /etc/nginx/nginx.conf

RUN chmod +x /usr/local/bin/venueless

COPY webapp/.* /venueless/webapp/
COPY webapp/*.js /venueless/webapp/
COPY webapp/*.json /venueless/webapp/
COPY webapp/*.html /venueless/webapp/
COPY webapp/src/ /venueless/webapp/src/
COPY webapp/public/ /venueless/webapp/public/
COPY webapp/build/ /venueless/webapp/build/

RUN cd /venueless/webapp && \
    npm ci && \
    npm run build && \
	mkdir -p data && \
	cd .. && \
    chown -R venueless:venueless /venueless /data

COPY server /venueless/server
WORKDIR /venueless/server
RUN python manage.py collectstatic --noinput

ARG COMMIT=""
LABEL commit=${COMMIT}
ENV VENUELESS_COMMIT_SHA=${COMMIT}

USER venueless
VOLUME ["/etc/venueless", "/data"]
EXPOSE 80
ENTRYPOINT ["venueless"]
CMD ["all"]

