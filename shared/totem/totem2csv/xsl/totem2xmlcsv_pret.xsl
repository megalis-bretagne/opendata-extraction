<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe Personnel file into CSV like XML file

TOTEM: http://odm-budgetaire.org/

author: Vincent Kober, Données et Cie Grenoble
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
               <column name="CodTypPret"/>
               <column name="NomBenefPret"/>
               <column name="DtDelib"/>
               <column name="MtCapitalRestDu_31_12"/>
               <column name="MtCapitalExer"/>
               <column name="MtIntExer"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:PRET">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:CodTypPret">
                          <cell name="CodTypPret" value="{totem:CodTypPret/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NomBenefPret">
                          <cell name="NomBenefPret" value="{totem:NomBenefPret/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DtDelib">
                          <cell name="DtDelib" value="{totem:DtDelib/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtCapitalRestDu_31_12">
                          <cell name="MtCapitalRestDu_31_12" value="{totem:MtCapitalRestDu_31_12/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtCapitalExer">
                          <cell name="MtCapitalExer" value="{totem:MtCapitalExer/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtIntExer">
                          <cell name="MtIntExer" value="{totem:MtIntExer/@V}" />
                        </xsl:if>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:PRET">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
