module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    clean : {
      dist : [
        'static/lib/*/*',
        'static/lib/*/.*',
        '!static/lib/*/dist',
        '!static/lib/*/js',
        'static/lib/bootstrap/js',
        '!static/lib/*/css',
        '!static/lib/pdfmake/build',
        '!static/lib/font-awesome/css',
        '!static/lib/font-awesome/fonts',
        '!static/lib/bootstrap-tour/build'
      ]
    }
  });

  grunt.loadNpmTasks('grunt-contrib-clean');
};
