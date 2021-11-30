<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe Organisme eng file into CSV like XML file

TOTEM: http://odm-budgetaire.org/

author: Pascal Romain - Rhizome-data
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:totem="http://www.minefi.gouv.fr/cp/demat/docbudgetaire">
  <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="/">
        <xsl:variable name="NatDec" select="//totem:BlocBudget/totem:NatDec/@V" />
        <xsl:variable name="Exer" select="//totem:BlocBudget/totem:Exer/@V" />
        <xsl:variable name="IdEtab" select="//totem:EnTeteBudget/totem:IdEtab/@V" />
        <xsl:variable name="LibelleColl" select="//totem:EnTeteDocBudgetaire/totem:LibelleColl/@V" />
        <csv>
            <header>
                <column name="BGT_NATDEC"/>
                <column name="BGT_ANNEE"/>
                <column name="BGT_SIRET"/>
                <column name="BGT_NOM"/>
                <column name="CodNatEng"/>
                <column name="NatEng"/>
                <column name="NomOrgEng"/>
                <column name="NatJurOrgEng"/>
                <column name="MtOrgEng"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:ORGANISME_ENG">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:BGT_NATDEC">
                          <cell name="BGT_NATDEC" value="{totem:BGT_NATDEC/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_ANNEE">
                          <cell name="BGT_ANNEE" value="{totem:BGT_ANNEE/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_SIRET">
                          <cell name="BGT_SIRET" value="{totem:BGT_SIRET/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_NOM">
                          <cell name="BGT_NOM" value="{totem:BGT_NOM/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodNatEng">
                          <cell name="CodNatEng" value="{totem:CodNatEng/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NatEng">
                          <cell name="NatEng" value="{totem:NatEng/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NomOrgEng">
                          <cell name="NomOrgEng" value="{totem:NomOrgEng/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NatJurOrgEng">
                          <cell name="NatJurOrgEng" value="{totem:NatJurOrgEng/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtOrgEng">
                          <cell name="MtOrgEng" value="{totem:MtOrgEng/@V}" />
                        </xsl:if>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:ORGANISME_ENG">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
