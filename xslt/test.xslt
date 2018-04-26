<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <xsl:import href="base.xslt" />
  <xsl:output omit-xml-declaration="yes" method="xhtml" indent="yes"/>

  <!-- Transform <foreign xml:lang="zap"> so that we can test FLEx insertion. -->
  <xsl:template match="tei:foreign[@xml:lang='zap']">
    <mark class="trigger">
      <xsl:apply-templates/>
    </mark>
  </xsl:template>
</xsl:stylesheet>
