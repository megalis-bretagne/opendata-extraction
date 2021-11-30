<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe Emprunt file into CSV like XML file

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
               <column name="CodTypEmpr"/>
               <!--Type d'emprunt-->
               <column name="CodProfilAmort"/>
               <!--Profil amortissement-->
               <column name="CodArticle"/>
               <column name="AnEncaisse"/>
               <!--Année de mobilisation-->
               <column name="ObjEmpr"/>
               <column name="MtEmprOrig"/>
               <column name="DureeRest"/>
               <!--Durée résiduelle-->
               <column name="CodTypPreteur"/>
               <column name="LibOrgaPreteur"/>
               <!--Organisme prêteur-->
               <column name="CodPeriodRemb"/>
               <!--Périodicité remboursement-->
               <column name="CodTyptxInit"/>
               <!--Type taux initial-->
               <column name="CodTyptxDtVote"/>
               <!--Type taux à Date du vote-->
               <column name="IndexTxVariInit"/>
               <!--Type d'index (ex: Euribor, 3 mois, ...)-->
               <column name="TxActuaInit"/>
               <!--Taux actuariel initial-->
               <column name="IndexTxVariDtVote"/>
               <!--Index taux variable à date vote-->
               <column name="TxActua"/>
               <!--Taux actuariel à date vote-->
               <column name="MtIntExer"/>
               <!--Montant intérêts à verser dans l'exercice.-->
                <column name="MtCapitalExer"/>
                <!--Montant capital à rembourser dans l'exercice-->
               <column name="MtCapitalRestDu_01_01"/>
               <!--Capital restant dû au 01/01 ou début exercice-->
               <column name="MtICNE"/>
               <column name="MtCapitalRestDu_31_12"/>
               <column name="CodTypEmprGaranti"/>
               <!--Type d'emprunt garanti-->
               <column name="TotGarEchoirExer"/>
               <column name="AnnuitNetDette"/>
               <column name="ProvGarantiEmpr"/>
               <column name="RReelFon"/>
               <column name="NumContrat"/>
               <column name="Tot1Annuite"/>
               <column name="IndSousJacent"/>
               <column name="IndSousJacentDtVote"/>
               <column name="Structure"/>
               <!--Structure de l'emprunt-->
               <column name="StructureDtVote"/>
               <column name="DtSignInit"/>   
               <column name="DtEmission"/>
               <column name="Dt1RembInit"/>
               <column name="Txinit"/>
               <column name="RtAnticipe"/>
               <column name="MtSortie"/>
               <column name="Couverture"/>
               <column name="DureeContratInit"/>
               <column name="TxMini"/>
               <column name="TxMaxi"/>


               
            </header>
            <data>
                <xsl:for-each select=".//totem:EMPRUNT">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:CodTypEmpr">
                          <cell name="CodTypEmpr" value="{totem:CodTypEmpr/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodProfilAmort">
                          <xsl:variable name="CodProfilAmort">
                            <xsl:variable name="code" select="totem:CodProfilAmort/@V" />
                            <!-- Profil d'amortissement -->
                              <xsl:choose>
                                <xsl:when test="$code = 'C'">Annuel constant</xsl:when>
                                <xsl:when test="$code = 'P'">Annuel progressif</xsl:when>
                                <xsl:when test="$code = 'F'">In fine</xsl:when>
                                <xsl:when test="$code = 'S'">Semestriel</xsl:when>
                                <xsl:when test="$code = 'M'">Mensuel</xsl:when>
                                <xsl:when test="$code = 'X'">Autre</xsl:when>
                                <xsl:otherwise>Nature juridique inconnue: <xsl:value-of select="$code"/></xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable> 
                        </xsl:if>
                        <xsl:if test="totem:CodArticle">
                          <cell name="CodArticle" value="{totem:CodArticle/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:AnEncaisse">
                          <cell name="AnEncaisse" value="{totem:AnEncaisse/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:ObjEmpr">
                          <cell name="ObjEmpr" value="{totem:ObjEmpr/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtEmprOrig">
                          <cell name="MtEmprOrig" value="{totem:MtEmprOrig/@V}" />
                        </xsl:if>

                        <xsl:if test="totem:DureeRest">
                          <cell name="DureeRest" value="{totem:DureeRest/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodTypPreteur">
                          <xsl:variable name="CodTypPreteur">
                            <xsl:variable name="code" select="totem:CodTypPreteur/@V" />
                            <!-- Type de prêteur -->
                              <xsl:choose>
                                <xsl:when test="$code = '01'">Organismes de droit privé</xsl:when>
                                <xsl:when test="$code = '02'">Organismes de droit public</xsl:when>
                                <xsl:when test="$code = '03'">Emissions obligataires</xsl:when>
                                <xsl:otherwise>type de prêteur inconnu: <xsl:value-of select="$code"/></xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable> 
                        </xsl:if>
                        <xsl:if test="totem:LibOrgaPreteur">
                          <cell name="LibOrgaPreteur" value="{totem:LibOrgaPreteur/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodPeriodRemb">
                          <cell name="CodPeriodRemb" value="{totem:CodPeriodRemb/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodTyptxInit">

                          <xsl:variable name="CodTyptxInit">
                            <xsl:variable name="code" select="totem:CodTyptxInit/@V" />
                            <!-- Type de taux -->
                              <xsl:choose>
                                <xsl:when test="$code = 'F'">Fixe sur toute la durée</xsl:when>
                                <xsl:when test="$code = 'I'">Indexé sur toute la durée</xsl:when>
                                <xsl:when test="$code = 'H'">Avec tranches</xsl:when>
                                <xsl:when test="$code = 'O'">Avec options</xsl:when>
                                <xsl:when test="$code = 'P'">Préfixé</xsl:when>
                                <xsl:when test="$code = 'A'">Postfixé</xsl:when>
                                <xsl:when test="$code = 'X'">Autre</xsl:when>
                                <xsl:otherwise>type de taux inconnu: <xsl:value-of select="$code"/></xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable> 

                        </xsl:if>
                        <xsl:if test="totem:CodTyptxDtVote">
                          <cell name="CodTyptxDtVote" value="{totem:CodTyptxDtVote/@V}" />
                        </xsl:if>


                        <xsl:if test="totem:IndexTxVariInit">
                          <cell name="IndexTxVariInit" value="{totem:IndexTxVariInit/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TxActuaInit">
                          <cell name="TxActuaInit" value="{totem:TxActuaInit/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:IndexTxVariDtVote">
                          <cell name="IndexTxVariDtVote" value="{totem:IndexTxVariDtVote/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TxActua">
                          <cell name="TxActua" value="{totem:TxActua/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtIntExer">
                          <cell name="MtIntExer" value="{totem:MtIntExer/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtCapitalExer">
                          <cell name="MtCapitalExer" value="{totem:MtCapitalExer/@V}" />
                        </xsl:if>


                        <xsl:if test="totem:MtCapitalRestDu_01_01">
                          <cell name="MtCapitalRestDu_01_01" value="{totem:MtCapitalRestDu_01_01/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtICNE">
                          <cell name="MtICNE" value="{totem:MtICNE/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtCapitalRestDu_31_12">
                          <cell name="MtCapitalRestDu_31_12" value="{totem:MtCapitalRestDu_31_12/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodTypEmprGaranti">
                          <cell name="CodTypEmprGaranti" value="{totem:CodTypEmprGaranti/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TotGarEchoirExer">
                          <cell name="TotGarEchoirExer" value="{totem:TotGarEchoirExer/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:AnnuitNetDette">
                          <cell name="AnnuitNetDette" value="{totem:AnnuitNetDette/@V}" />
                        </xsl:if>

                        <xsl:if test="totem:ProvGarantiEmpr">
                          <cell name="ProvGarantiEmpr" value="{totem:ProvGarantiEmpr/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:RReelFon">
                          <cell name="RReelFon" value="{totem:RReelFon/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NumContrat">
                          <cell name="NumContrat" value="{totem:NumContrat/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:Tot1Annuite">
                          <cell name="Tot1Annuite" value="{totem:Tot1Annuite/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:IndSousJacent">
                          <cell name="IndSousJacent" value="{totem:IndSousJacent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:IndSousJacentDtVote">
                          <cell name="IndSousJacentDtVote" value="{totem:IndSousJacentDtVote/@V}" />
                        </xsl:if>

                        <xsl:if test="totem:Structure">
                          <cell name="Structure" value="{totem:Structure/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:StructureDtVote">
                          <cell name="StructureDtVote" value="{totem:StructureDtVote/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DtSignInit">
                          <cell name="DtSignInit" value="{totem:DtSignInit/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DtEmission">
                          <cell name="DtEmission" value="{totem:DtEmission/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:IndSousJacent">
                          <cell name="IndSousJacent" value="{totem:IndSousJacent/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:Dt1RembInit">
                          <cell name="Dt1RembInit" value="{totem:Dt1RembInit/@V}" />
                        </xsl:if>
                        
                        <xsl:if test="totem:Txinit">
                          <cell name="Txinit" value="{totem:Txinit/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:RtAnticipe">
                          <cell name="RtAnticipe" value="{totem:RtAnticipe/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtSortie">
                          <cell name="MtSortie" value="{totem:MtSortie/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:Couverture">
                          <cell name="Couverture" value="{totem:Couverture/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DureeContratInit">
                          <cell name="DureeContratInit" value="{totem:DureeContratInit/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TxMini">
                          <cell name="TxMini" value="{totem:TxMini/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:TxMaxi">
                          <cell name="TxMaxi" value="{totem:TxMaxi/@V}" />
                        </xsl:if>                        
                        
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:EMPRUNT">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
