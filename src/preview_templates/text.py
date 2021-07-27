TEXT_PREVIEW_TEMPLATE = """\
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <title>ticha-magic Text Preview</title>
    <link rel="stylesheet" href="https://ticha.haverford.edu/static/zapotexts/css/page_detail_style.css"/>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"/>
    <link rel="stylesheet" href="https://ticha.haverford.edu/static/css/custom.css"/>
</head>
  <body>
    <div class="container">
      <div class="row text-left">
        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
        </div>
        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
          {}
        </div>
      </div>
    </div>

    <script src="https://code.jquery.com/jquery-1.12.4.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.1.0/js/bootstrap.min.js"></script>
    <script src="https://ticha.haverford.edu/static/zapotexts/js/popovers.js"></script>
    <script src="https://ticha.haverford.edu/static/zapotexts/js/viewer_base.js"></script>
    <script src="https://ticha.haverford.edu/static/zapotexts/js/viewer_regular.js"></script>
    <script type="text/javascript">
        initPopovers()
    </script>


  </body>
</html>
"""
