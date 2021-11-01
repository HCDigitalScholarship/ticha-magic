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

  <!-- Transform <note> tags (add brackets and apply class) -->
  <xsl:template match="tei:note">
    <span class="note">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='margin left']">
    <span class="note marginalia-margin-left">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='margin right']">
    <span class="note marginalia-margin-right">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='above']">
    <span class="note marginalia-above">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='below']">
    <span class="note marginalia-below">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='top']">
    <span class="note marginalia-top">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:note[@place='bottom']">
    <span class="note marginalia-bottom">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <!-- Transform <add> tags (add brackets and apply class) -->
  <xsl:template match="tei:add">
    <span class="add">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='margin left']">
    <span class="add marginalia-margin-left">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='margin right']">
    <span class="add marginalia-margin-right">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='above']">
    <span class="add marginalia-above">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='below']">
    <span class="add marginalia-below">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='top']">
    <span class="add marginalia-top">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>

  <xsl:template match="tei:add[@place='bottom']">
    <span class="add marginalia-bottom">
      {<xsl:apply-templates/>}
    </span>
  </xsl:template>


</xsl:stylesheet>
