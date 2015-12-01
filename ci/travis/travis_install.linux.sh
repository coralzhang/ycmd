# Linux-specific installation

# We can't use sudo, so we have to approximate the behaviour of the following:
# $ sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-6 90

mkdir ${HOME}/bin

ln -s /usr/bin/g++-6 ${HOME}/bin/c++
ln -s /usr/bin/gcc-6 ${HOME}/bin/cc

export PATH=${HOME}/bin:${PATH}

# In order to work with ycmd, python *must* be built as a shared library. This
# is set via the PYTHON_CONFIGURE_OPTS option.
export PYTHON_CONFIGURE_OPTS="--enable-shared"

# Install PHP
if [ ! -e "${HOME}/.phpenv/versions/${PHP_VERSION}/bin/php" ]; then
  # Travis caching will create the folder whether it contains files or not. We need
  # to remove it for cloning repositories.
  rm -rf "${HOME}/.phpenv"
  git clone https://github.com/madumlao/phpenv.git ${HOME}/.phpenv
  git clone https://github.com/php-build/php-build ${HOME}/.phpenv/plugins/php-build
  # TODO: try to remove this line
  # export PATH=${HOME}/.phpenv/shims:${HOME}/.phpenv/bin:${PATH}

  # Prefix Travis script to avoid a build timeout because compiling PHP may not
  # produce any output for more than 10 minutes.
  travis_wait ${HOME}/.phpenv/bin/phpenv install ${PHP_VERSION}
fi

export PATH=${HOME}/.phpenv/versions/${PHP_VERSION}/bin:${PATH}
