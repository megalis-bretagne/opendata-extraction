<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe APCP file into CSV like XML file

TOTEM: http://odm-budgetaire.org/

author: Pascal Romain, Rhizome-data
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
               <column name="CodTypAutori"/>
               <column name="CodSTypAutori"/>
               <column name="NumAutori"/>
               <column name="LibAutori"/>
               <column name="Chapitre"/>
               <column name="MtAutoriPropose"/>
               <column name="MtAutoriVote"/>
               <column name="TypeChapitre"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:APCP">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:CodTypAutori">
                          <cell name="CodTypAutori" value="{totem:CodTypAutori/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodSTypAutori">
                          <cell name="CodSTypAutori" value="{totem:CodSTypAutori/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NumAutori">
                          <cell name="NumAutori" value="{totem:NumAutori/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:LibAutori">
                          <cell name="LibAutori" value="{totem:LibAutori/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:Chapitre">
                          <cell name="Chapitre" value="{totem:Chapitre/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtAutoriPropose">
                          <cell name="MtAutoriPropose" value="{totem:MtAutoriPropose/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtAutoriVote">
                          <cell name="MtAutoriVote" value="{totem:MtAutoriVote/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TypeChapitre">
                          <cell name="TypeChapitre" value="{totem:TypeChapitre/@V}" />
                        </xsl:if>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:APCP">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
