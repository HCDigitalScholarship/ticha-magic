<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <xsl:import href="base.xslt" />
  <xsl:output omit-xml-declaration="yes" method="xhtml" indent="yes"/>


  <!-- Transform <foreign> tags -->
  <xsl:template match="tei:foreign[@xml:lang='zap']">
    <span class="zap">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:foreign[@xml:lang='lat']">
    <span class="lat">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

</xsl:stylesheet>
